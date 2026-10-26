import { Component, ChangeDetectionStrategy } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { Backend } from './services/backend';

@Component({
    selector: 'app-root',
    imports: [RouterOutlet, RouterLink],
    templateUrl: './app.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './app.scss',
})
export class App {
    constructor(
        public backend: Backend,
        private router: Router,
    ) {}

    protected removeMessage(idx: number) {
        this.backend.messages.update((messages) => messages.filter((_, i) => i !== idx));
    }

    protected logout() {
        this.backend.logout().subscribe({
            next: (response) => {
                if (response.ok) {
                    this.router.navigate(['/']);
                }
            },
            error: this.backend.defaultErrorHandler,
        });
    }
}
