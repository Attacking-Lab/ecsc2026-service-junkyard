import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Junk } from './junk';

describe('Junk', () => {
    let component: Junk;
    let fixture: ComponentFixture<Junk>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [Junk],
        }).compileComponents();

        fixture = TestBed.createComponent(Junk);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
