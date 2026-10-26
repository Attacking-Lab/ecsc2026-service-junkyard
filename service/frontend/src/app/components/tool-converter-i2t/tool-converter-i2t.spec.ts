import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolConverterI2t } from './tool-converter-i2t';

describe('ToolConverterI2t', () => {
    let component: ToolConverterI2t;
    let fixture: ComponentFixture<ToolConverterI2t>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolConverterI2t],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolConverterI2t);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
