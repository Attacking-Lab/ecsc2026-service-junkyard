import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImgWithRect } from './img-with-rect';

describe('ImgWithRect', () => {
    let component: ImgWithRect;
    let fixture: ComponentFixture<ImgWithRect>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ImgWithRect],
        }).compileComponents();

        fixture = TestBed.createComponent(ImgWithRect);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
