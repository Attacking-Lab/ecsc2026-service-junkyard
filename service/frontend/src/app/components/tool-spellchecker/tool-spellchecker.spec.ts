import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolSpellchecker } from './tool-spellchecker';

describe('ToolSpellchecker', () => {
    let component: ToolSpellchecker;
    let fixture: ComponentFixture<ToolSpellchecker>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolSpellchecker],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolSpellchecker);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
