import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolCropper } from './tool-cropper';

describe('ToolCropper', () => {
    let component: ToolCropper;
    let fixture: ComponentFixture<ToolCropper>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolCropper],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolCropper);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
