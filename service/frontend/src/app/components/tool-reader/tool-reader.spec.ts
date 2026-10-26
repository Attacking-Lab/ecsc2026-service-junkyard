import {ComponentFixture, TestBed} from '@angular/core/testing';

import {ToolReader} from './tool-reader';

describe('ToolReader', () => {
    let component: ToolReader;
    let fixture: ComponentFixture<ToolReader>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ToolReader],
        }).compileComponents();

        fixture = TestBed.createComponent(ToolReader);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
