import {
    Component,
    Input,
    OnDestroy,
    signal,
    WritableSignal,
    ChangeDetectionStrategy,
} from '@angular/core';
import { Backend } from '../../services/backend';

@Component({
    selector: 'app-tool-inspector',
    imports: [],
    templateUrl: './tool-inspector.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-inspector.scss',
})
export class ToolInspector implements OnDestroy {
    @Input() id: string = '';
    @Input() meta: string = '';
    blobUrl: WritableSignal<string | null> = signal(null);

    constructor(public backend: Backend) {}

    run() {
        this.backend.processBlob('Inspector', this.id, this.meta).subscribe({
            next: (blob) => {
                this.backend.alert('Inspector invoked', 'success');
                if (this.blobUrl()) {
                    URL.revokeObjectURL(this.blobUrl()!);
                }
                this.blobUrl.set(URL.createObjectURL(blob));
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    ngOnDestroy() {
        if (this.blobUrl()) {
            URL.revokeObjectURL(this.blobUrl()!);
        }
    }
}
