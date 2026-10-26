import {
    Component,
    Input,
    signal,
    WritableSignal,
    ChangeDetectionStrategy,
} from '@angular/core';
import {Backend} from '../../services/backend';
import {Router} from '@angular/router';


export function randomString() {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    const charactersLength = characters.length;
    for (let i = 0; i < 16; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}


@Component({
    selector: 'app-tool-converter-i2t',
    imports: [],
    templateUrl: './tool-converter-i2t.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-converter-i2t.scss',
})
export class ToolConverterI2t {
    @Input() id: string = '';
    @Input() meta: string = '';

    content: WritableSignal<string | null> = signal(null);

    constructor(
        public backend: Backend,
        private router: Router,
    ) {
    }

    protected run() {
        let userdata = {action: 'ITT', path: randomString() + '.txt'};
        this.backend.processString('Converter', this.id, this.meta, userdata).subscribe({
            next: (response) => {
                this.content.set(response);
                this.backend.alert('Converter successful', 'success');
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    protected save() {
        let f = new File([this.content()!], 'output.txt', {type: 'text/plain'});
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
