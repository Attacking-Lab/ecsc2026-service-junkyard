import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolCensor } from './tool-censor';

describe('ToolCensor', () => {
    let component: ToolCensor;
    let fixture: ComponentFixture<ToolCensor>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolCensor],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolCensor);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
