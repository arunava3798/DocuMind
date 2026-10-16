import { Component, OnInit, inject, output, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';

import { DocumentInfo } from '../../models/api.models';
import { RagService } from '../../services/rag.service';

@Component({
  selector: 'app-document-manager',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './document-manager.html',
  styleUrl: './document-manager.scss',
})
export class DocumentManager implements OnInit {
  private rag = inject(RagService);

  documents = signal<DocumentInfo[]>([]);
  selected = signal<File[]>([]);
  uploading = signal(false);
  error = signal<string | null>(null);

  changed = output<void>();

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.rag.listDocuments().subscribe({
      next: (docs) => this.documents.set(docs),
      error: () => this.error.set('Could not reach the backend.'),
    });
  }

  onFiles(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selected.set(input.files ? Array.from(input.files) : []);
  }

  upload(): void {
    const files = this.selected();
    if (!files.length || this.uploading()) {
      return;
    }
    this.uploading.set(true);
    this.error.set(null);
    this.rag.ingest(files).subscribe({
      next: () => {
        this.uploading.set(false);
        this.selected.set([]);
        this.refresh();
        this.changed.emit();
      },
      error: () => {
        this.uploading.set(false);
        this.error.set('Upload failed.');
      },
    });
  }

  remove(id: string): void {
    this.rag.deleteDocument(id).subscribe({
      next: () => {
        this.refresh();
        this.changed.emit();
      },
      error: () => this.error.set('Delete failed.'),
    });
  }
}
