import { Component, viewChild } from '@angular/core';

import { Chat } from './components/chat/chat';
import { DocumentManager } from './components/document-manager/document-manager';

@Component({
  selector: 'app-root',
  imports: [Chat, DocumentManager],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = 'DocuMind';
  readonly chatRef = viewChild(Chat);

  clearChat(): void {
    this.chatRef()?.clear();
  }
}
