import {
    Component,
    EventEmitter,
    Input,
    Output,
    signal,
    WritableSignal,
    ChangeDetectionStrategy,
} from '@angular/core';

export interface RectCoords {
    x: number;
    y: number;
    w: number;
    h: number;
}

export interface Dimensions {
    w: number;
    h: number;
}

@Component({
    selector: 'app-img-with-rect',
    imports: [],
    templateUrl: './img-with-rect.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './img-with-rect.scss',
})
export class ImgWithRect {
    @Input() url!: string;

    @Input() color: string = '';

    imageSize: WritableSignal<Dimensions> = signal({ x: 0, y: 0, w: 0, h: 0 });
    rect: RectCoords = { x: 0, y: 0, w: 0, h: 0 };

    @Output('imagesize') imageSizeEvent = new EventEmitter<Dimensions>();
    @Output('rect') rectEvent = new EventEmitter<RectCoords>();

    onImageLoad(e: Event) {
        this.imageSize.set({ w: (e.target! as any).width, h: (e.target! as any).height });
        this.rect = { x: 0, y: 0, w: (e.target! as any).width, h: (e.target! as any).height };
        this.imageSizeEvent.emit(this.imageSize());
        this.rectEvent.emit(this.rect);
    }

    private dragLimits = { x1: 0, y1: 0, x2: 0, y2: 0 };
    protected dragX: string | boolean = false;
    protected dragY: string | boolean = false;
    private initialDrag = { x: 0, y: 0 };
    private minimalDimensions = 10;

    startDrag($event: MouseEvent, c1: string, c2: string) {
        this.dragLimits = { x1: 0, y1: 0, x2: this.imageSize().w, y2: this.imageSize().h };
        this.initialDrag = { x: $event.pageX - this.rect.x, y: $event.pageY - this.rect.y };
        this.dragX = c1;
        this.dragY = c2;
        if (c1 == 'w') {
            this.dragLimits.x1 = this.rect.x + this.minimalDimensions;
            this.initialDrag.x -= this.rect.w;
        } else {
            this.dragLimits.x2 -= this.minimalDimensions;
        }
        if (c2 == 'h') {
            this.dragLimits.y1 = this.rect.y + this.minimalDimensions;
            this.initialDrag.y -= this.rect.h;
        } else {
            this.dragLimits.y2 -= this.minimalDimensions;
        }
    }

    endDrag($event: MouseEvent) {
        this.dragX = false;
        this.dragY = false;
    }

    drag($event: MouseEvent) {
        let x = $event.pageX - this.initialDrag.x;
        let y = $event.pageY - this.initialDrag.y;
        x = Math.max(this.dragLimits.x1, Math.min(this.dragLimits.x2, x));
        y = Math.max(this.dragLimits.y1, Math.min(this.dragLimits.y2, y));
        if (this.dragX == 'x') {
            let x2 = this.rect.x + this.rect.w;
            this.rect.x = x;
            this.rect.w = x2 - x;
        } else if (this.dragX == 'w') {
            this.rect.w = x - this.rect.x;
        } else {
            return;
        }
        if (this.dragY == 'y') {
            let y2 = this.rect.y + this.rect.h;
            this.rect.y = y;
            this.rect.h = y2 - y;
        } else if (this.dragY == 'h') {
            this.rect.h = y - this.rect.y;
        } else {
            return;
        }
        this.rectEvent.emit(this.rect);
    }
}
