import { Component, Input, signal, WritableSignal, ChangeDetectionStrategy } from '@angular/core';
import { Backend } from '../../services/backend';

@Component({
    selector: 'app-tool-reader',
    imports: [],
    templateUrl: './tool-reader.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-reader.scss',
})
export class ToolReader {
    @Input() id: string = '';
    @Input() meta: string = '';
    content: WritableSignal<string | null> = signal(null);

    constructor(public backend: Backend) {}

    run() {
        this.backend.processString('Reader', this.id, this.meta).subscribe({
            next: (content) => {
                this.backend.alert('Reader invoked', 'success');
                this.content.set(content);
            },
            error: this.backend.defaultErrorHandler,
        });
    }
}
