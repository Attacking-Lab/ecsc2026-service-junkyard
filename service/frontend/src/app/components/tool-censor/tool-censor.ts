import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { ImgWithRect, RectCoords } from '../img-with-rect/img-with-rect';
import { Backend } from '../../services/backend';
import { Router } from '@angular/router';

@Component({
    selector: 'app-tool-censor',
    imports: [ImgWithRect],
    templateUrl: './tool-censor.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-censor.scss',
})
export class ToolCensor {
    @Input() id: string = '';
    @Input() meta: string = '';
    @Output('meta') metaEvent = new EventEmitter<string>();

    protected rect: RectCoords = { x: 0, y: 0, w: 0, h: 0 };

    constructor(
        public backend: Backend,
        private router: Router,
    ) {}

    protected run() {
        this.backend.process<string>('Censor', this.id, this.meta, this.rect).subscribe({
            next: (response) => {
                this.meta = response;
                this.metaEvent.emit(this.meta);
                this.backend.alert('Censor successful', 'success');
                this.router.navigate(['/junk', this.id, this.meta]);
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    protected updateRect(rect: RectCoords) {
        this.rect = rect;
    }
}
