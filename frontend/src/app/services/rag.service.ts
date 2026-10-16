import { HttpClient, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  ChatMessage,
  ChatResponse,
  ChatResult,
  DocumentInfo,
  IngestResponse,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class RagService {
  private http = inject(HttpClient);
  private readonly base = environment.apiBase;

  listDocuments(): Observable<DocumentInfo[]> {
    return this.http.get<DocumentInfo[]>(`${this.base}/api/documents`);
  }

  ingest(files: File[]): Observable<IngestResponse> {
    const form = new FormData();
    files.forEach((file) => form.append('files', file));
    return this.http.post<IngestResponse>(`${this.base}/api/documents/ingest`, form);
  }

  deleteDocument(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/documents/${id}`);
  }

  chat(question: string, history: ChatMessage[]): Observable<ChatResult> {
    return this.http
      .post<ChatResponse>(
        `${this.base}/api/chat`,
        { question, history },
        { observe: 'response' },
      )
      .pipe(map((response) => this.toResult(response)));
  }

  private toResult(response: HttpResponse<ChatResponse>): ChatResult {
    const body = response.body!;
    return {
      answer: body.answer,
      sources: body.sources,
      meta: {
        processTimeMs: this.numberOrUndefined(response.headers.get('X-Process-Time-Ms')),
        totalTokens: this.numberOrUndefined(response.headers.get('X-LLM-Total-Tokens')),
        estCostUsd: this.numberOrUndefined(response.headers.get('X-Est-Cost-USD')),
      },
    };
  }

  private numberOrUndefined(value: string | null): number | undefined {
    if (value === null) {
      return undefined;
    }
    const parsed = Number(value);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
}
