import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { Backend } from '../../services/backend';
import { Dimensions, ImgWithRect, RectCoords } from '../img-with-rect/img-with-rect';
import { Router } from '@angular/router';

@Component({
    selector: 'app-tool-cropper',
    imports: [ImgWithRect],
    templateUrl: './tool-cropper.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-cropper.scss',
})
export class ToolCropper {
    @Input() id: string = '';
    @Input() meta: string = '';
    @Output('meta') metaEvent = new EventEmitter<string>();

    protected dimensions: Dimensions = { w: 0, h: 0 };
    protected rect: RectCoords = { x: 0, y: 0, w: 0, h: 0 };

    constructor(
        public backend: Backend,
        private router: Router,
    ) {}

    protected run() {
        let data = {
            t: this.rect.y,
            r: this.dimensions.w - this.rect.x - this.rect.w,
            b: this.dimensions.h - this.rect.y - this.rect.h,
            l: this.rect.x,
        };
        this.backend.process<string>('Cropper', this.id, this.meta, data).subscribe({
            next: (response) => {
                this.meta = response;
                this.metaEvent.emit(this.meta);
                this.backend.alert('Cropper successful', 'success');
                this.router.navigate(['/junk', this.id, this.meta]);
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    protected updateRect(rect: RectCoords) {
        this.rect = rect;
    }

    protected updateDimensions(dimensions: Dimensions) {
        this.dimensions = dimensions;
    }
}
