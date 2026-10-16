export interface DocumentInfo {
  id: string;
  filename: string;
  chunk_count: number;
  size_bytes: number;
  created_at: string;
}

export interface IngestResponse {
  ingested_files: string[];
  total_chunks: number;
  documents: DocumentInfo[];
}

export interface SourceChunk {
  source: string;
  content: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
}

export interface ChatMeta {
  processTimeMs?: number;
  totalTokens?: number;
  estCostUsd?: number;
}

export interface ChatResult {
  answer: string;
  sources: SourceChunk[];
  meta: ChatMeta;
}
