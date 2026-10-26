import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolInspector } from './tool-inspector';

describe('ToolInspector', () => {
    let component: ToolInspector;
    let fixture: ComponentFixture<ToolInspector>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolInspector],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolInspector);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
