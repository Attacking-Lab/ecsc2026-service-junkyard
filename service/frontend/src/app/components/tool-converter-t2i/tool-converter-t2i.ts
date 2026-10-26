import {
    Component,
    EventEmitter,
    Input,
    Output,
    signal,
    WritableSignal,
    ChangeDetectionStrategy,
} from '@angular/core';
import { Backend } from '../../services/backend';
import { Router } from '@angular/router';
import {randomString} from '../tool-converter-i2t/tool-converter-i2t';


@Component({
    selector: 'app-tool-converter-t2i',
    imports: [],
    templateUrl: './tool-converter-t2i.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-converter-t2i.scss',
})
export class ToolConverterT2i {
    @Input() id: string = '';
    @Input() meta: string = '';
    @Output('meta') metaEvent = new EventEmitter<string>();

    blobUrl: WritableSignal<string | null> = signal(null);
    private blob: Blob | null = null;

    constructor(
        public backend: Backend,
        private router: Router,
    ) {}

    protected run() {
        let userdata = { action: 'TTI', path: randomString() + '.bmp' };
        this.backend.processBlob('Converter', this.id, this.meta, userdata).subscribe({
            next: (blob) => {
                if (this.blobUrl()) {
                    URL.revokeObjectURL(this.blobUrl()!);
                }
                this.blob = blob;
                this.blobUrl.set(URL.createObjectURL(blob));
                this.backend.alert('Converter successful', 'success');
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    protected save() {
        let f = new File([this.blob!], 'output.bmp', { type: 'image/bmp' });
        this.backend.upload(f).subscribe({
            next: (response) => {
                if (response.ok) {
                    this.backend.alert(`Uploaded junk ${response.filename}`);
                    this.router.navigate(['/junk', response.filename!]);
                }
            },
            error: this.backend.defaultErrorHandler,
        });
    }
}
