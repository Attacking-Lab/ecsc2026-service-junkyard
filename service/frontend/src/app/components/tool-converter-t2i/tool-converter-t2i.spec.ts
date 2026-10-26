import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolConverterT2i } from './tool-converter-t2i';

describe('ToolConverterT2i', () => {
    let component: ToolConverterT2i;
    let fixture: ComponentFixture<ToolConverterT2i>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolConverterT2i],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolConverterT2i);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
