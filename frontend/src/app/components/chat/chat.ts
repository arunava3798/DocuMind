import { Component, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ChatMessage, ChatMeta, SourceChunk } from '../../models/api.models';
import { RagService } from '../../services/rag.service';

interface DisplayMessage extends ChatMessage {
  sources?: SourceChunk[];
  meta?: ChatMeta;
}

@Component({
  selector: 'app-chat',
  imports: [FormsModule, DecimalPipe],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
})
export class Chat {
  private rag = inject(RagService);

  messages = signal<DisplayMessage[]>([]);
  input = signal('');
  loading = signal(false);
  error = signal<string | null>(null);

  clear(): void {
    this.messages.set([]);
    this.input.set('');
    this.error.set(null);
    this.loading.set(false);
  }

  send(): void {
    const question = this.input().trim();
    if (!question || this.loading()) {
      return;
    }

    const history: ChatMessage[] = this.messages().map((m) => ({
      role: m.role,
      content: m.content,
    }));

    this.messages.update((list) => [...list, { role: 'user', content: question }]);
    this.input.set('');
    this.loading.set(true);
    this.error.set(null);

    this.rag.chat(question, history).subscribe({
      next: (result) => {
        this.messages.update((list) => [
          ...list,
          {
            role: 'assistant',
            content: result.answer,
            sources: result.sources,
            meta: result.meta,
          },
        ]);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Request failed. Is the backend running at the configured URL?');
        this.loading.set(false);
      },
    });
  }
}
