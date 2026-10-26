import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Backend } from '../../services/backend';

@Component({
    selector: 'app-frontpage',
    imports: [FormsModule],
    templateUrl: './frontpage.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './frontpage.scss',
})
export class Frontpage implements OnInit {
    public username: string = '';
    public password: string = '';
    public firstName: string = '';
    public lastName: string = '';
    protected tab: string = 'login';

    constructor(
        public backend: Backend,
        private router: Router,
    ) {}

    ngOnInit(): void {
        this.backend.me().subscribe(() => this.router.navigate(['/user']));
    }

    public login() {
        this.backend.login(this.username, this.password).subscribe({
            next: (response) => {
                if (response.ok) {
                    this.router.navigate(['/user']);
                }
            },
            error: this.backend.defaultErrorHandler,
        });
    }

    public register() {
        this.backend
            .register(this.username, this.password, this.firstName, this.lastName)
            .subscribe({
                next: (response) => {
                    if (response.ok) {
                        this.router.navigate(['/user']);
                    }
                },
                error: this.backend.defaultErrorHandler,
            });
    }
}
