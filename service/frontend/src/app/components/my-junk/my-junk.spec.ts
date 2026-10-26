import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyJunk } from './my-junk';

describe('MyJunk', () => {
    let component: MyJunk;
    let fixture: ComponentFixture<MyJunk>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [MyJunk],
        }).compileComponents();

        fixture = TestBed.createComponent(MyJunk);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
