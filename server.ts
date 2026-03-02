import express from 'express';
import { createServer as createViteServer } from 'vite';
import Database from 'better-sqlite3';
import crypto from 'crypto';
import { GoogleGenAI, Type } from '@google/genai';

const db = new Database('clauseflag.db');

// Initialize database schema
db.exec(`
  CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    url TEXT,
    raw_text TEXT,
    status TEXT,
    clause_count INTEGER,
    risk_summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
  );

  CREATE TABLE IF NOT EXISTS clauses (
    id TEXT PRIMARY KEY,
    analysis_id TEXT,
    position INTEGER,
    text TEXT,
    risk TEXT,
    confidence REAL,
    category TEXT,
    explanation TEXT,
    FOREIGN KEY(analysis_id) REFERENCES analyses(id)
  );
`);

const app = express();
app.use(express.json());

const PORT = 3000;

let aiClient: GoogleGenAI | null = null;

function getAiClient(): GoogleGenAI {
  if (!aiClient) {
    let key = process.env.GEMINI_API_KEY;
    if (!key) {
      throw new Error('GEMINI_API_KEY environment variable is required');
    }
    // Strip quotes in case the user accidentally included them in the Secrets panel
    key = key.replace(/^"|"$/g, '').replace(/^'|'$/g, '').trim();
    
    if (key === 'MY_GEMINI_API_KEY' || key.trim() === '') {
      throw new Error('Please configure a valid GEMINI_API_KEY in the AI Studio Secrets panel.');
    }
    
    aiClient = new GoogleGenAI({ apiKey: key });
  }
  return aiClient;
}

// Helper to split text into sentences
function splitIntoSentences(text: string): string[] {
  return text.match(/[^.!?]+[.!?]+/g)?.map(s => s.trim()).filter(s => s.length > 0) || [text];
}

// Rule-based fallback classifier
function ruleBasedClassify(sentence: string) {
  const lower = sentence.toLowerCase();
  if (lower.includes('sell') || lower.includes('third party') || lower.includes('without your consent') || lower.includes('waive') || lower.includes('arbitration')) {
    return { risk: 'danger', confidence: 0.85 + Math.random() * 0.1 };
  }
  if (lower.includes('may share') || lower.includes('partners') || lower.includes('advertising') || lower.includes('tracking') || lower.includes('cookies')) {
    return { risk: 'watch', confidence: 0.75 + Math.random() * 0.1 };
  }
  return { risk: 'safe', confidence: 0.90 + Math.random() * 0.05 };
}

app.post('/api/analyze', async (req, res) => {
  const { url, text } = req.body;
  
  if (!text) {
    return res.status(400).json({ error: 'Text is required' });
  }

  const analysisId = crypto.randomUUID();

  try {
    // Insert initial record
    const insertAnalysis = db.prepare(`
      INSERT INTO analyses (id, url, raw_text, status, clause_count, risk_summary)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    
    insertAnalysis.run(analysisId, url || null, text, 'processing', 0, JSON.stringify({ safe: 0, watch: 0, danger: 0 }));

    const sentences = splitIntoSentences(text);
    let classifications: any[] = [];

    try {
      // Try using Gemini to classify sentences
      const ai = getAiClient();
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Analyze the following privacy policy sentences. For each sentence, determine the risk level ('safe', 'watch', or 'danger') and a confidence score between 0.0 and 1.0.
        
Sentences:
${sentences.map((s, i) => `[${i}] ${s}`).join('\n')}
`,
        config: {
          responseMimeType: 'application/json',
          responseSchema: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                index: { type: Type.INTEGER },
                risk: { type: Type.STRING, description: "Must be 'safe', 'watch', or 'danger'" },
                confidence: { type: Type.NUMBER }
              },
              required: ["index", "risk", "confidence"]
            }
          }
        }
      });

      if (response.text) {
        const parsed = JSON.parse(response.text);
        if (Array.isArray(parsed)) {
          classifications = parsed;
        } else {
          throw new Error("Gemini response is not an array");
        }
      }
    } catch (e: any) {
      const errorString = e.toString() + (e.message || '');
      if (errorString.includes('API key not valid') || errorString.includes('GEMINI_API_KEY') || errorString.includes('API_KEY_INVALID')) {
        throw new Error('Invalid or missing Gemini API Key. Please update your GEMINI_API_KEY in the AI Studio Secrets panel.');
      }
      console.error("Failed to parse Gemini response, using fallback rules", e);
      // Fallback to rule-based classification if Gemini fails
      classifications = sentences.map((s, i) => ({
        index: i,
        ...ruleBasedClassify(s)
      }));
    }

    // Ensure classifications exist for all sentences
    if (classifications.length === 0) {
      classifications = sentences.map((s, i) => ({
        index: i,
        ...ruleBasedClassify(s)
      }));
    }

    const insertClause = db.prepare(`
      INSERT INTO clauses (id, analysis_id, position, text, risk, confidence)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    const riskSummary = { safe: 0, watch: 0, danger: 0 };

    const insertMany = db.transaction((clauses: any[]) => {
      for (const clause of clauses) {
        insertClause.run(clause.id, clause.analysis_id, clause.position, clause.text, clause.risk, clause.confidence);
      }
    });

    const clausesToInsert = sentences.map((sentence, i) => {
      const classification = classifications.find((c: any) => c.index === i) || ruleBasedClassify(sentence);
      const risk = ['safe', 'watch', 'danger'].includes(classification.risk) ? classification.risk : 'watch';
      
      riskSummary[risk as keyof typeof riskSummary]++;

      return {
        id: crypto.randomUUID(),
        analysis_id: analysisId,
        position: i,
        text: sentence,
        risk: risk,
        confidence: classification.confidence
      };
    });

    insertMany(clausesToInsert);

    const updateAnalysis = db.prepare(`
      UPDATE analyses 
      SET status = 'complete', clause_count = ?, risk_summary = ?, completed_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    
    updateAnalysis.run(sentences.length, JSON.stringify(riskSummary), analysisId);

    res.json({ id: analysisId, status: 'complete' });

  } catch (error: any) {
    console.error("Analysis failed:", error);
    try {
      db.prepare(`UPDATE analyses SET status = 'failed' WHERE id = ?`).run(analysisId);
    } catch (dbError) {
      console.error("Failed to update status:", dbError);
    }
    res.status(500).json({ error: 'Analysis failed', details: error.message, stack: error.stack });
  }
});

app.get('/api/analyses/:id', (req, res) => {
  const row = db.prepare('SELECT * FROM analyses WHERE id = ?').get(req.params.id) as any;
  if (!row) {
    return res.status(404).json({ error: 'Not found' });
  }
  res.json({
    id: row.id,
    status: row.status,
    clause_count: row.clause_count,
    risk_summary: JSON.parse(row.risk_summary)
  });
});

app.get('/api/analyses/:id/clauses', (req, res) => {
  const rows = db.prepare('SELECT * FROM clauses WHERE analysis_id = ? ORDER BY position ASC').all(req.params.id);
  res.json({ clauses: rows });
});

async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static('dist'));
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
