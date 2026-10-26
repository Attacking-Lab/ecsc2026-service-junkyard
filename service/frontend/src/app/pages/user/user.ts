import { Component, effect, ChangeDetectionStrategy } from '@angular/core';
import { Backend, UserResponse } from '../../services/backend';
import { Router } from '@angular/router';
import { AsyncPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { MyJunk } from '../../components/my-junk/my-junk';

@Component({
    selector: 'app-user',
    imports: [AsyncPipe, FormsModule, MyJunk],
    templateUrl: './user.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './user.scss',
})
export class User {
    response$!: Observable<UserResponse>;

    junkIdentifier: string = '';

    constructor(
        public backend: Backend,
        private router: Router,
    ) {
        effect(() => {
            // No error handling because FU angular
            this.response$ = this.backend.me();
        });
    }

    lookup(id: string) {
        if (id.includes('/')) {
            let parts = id.split('/');
            this.router.navigate(['/junk', parts[0], parts[1]]);
        } else {
            this.router.navigate(['/junk', id]);
        }
    }
}
