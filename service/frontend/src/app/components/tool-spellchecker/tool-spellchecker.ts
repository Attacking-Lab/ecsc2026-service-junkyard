import { Component, Input, signal, WritableSignal, ChangeDetectionStrategy } from '@angular/core';
import { Backend } from '../../services/backend';
import { FormsModule } from '@angular/forms';

@Component({
    selector: 'app-tool-spellchecker',
    imports: [FormsModule],
    templateUrl: './tool-spellchecker.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './tool-spellchecker.scss',
})
export class ToolSpellchecker {
    @Input() id: string = '';
    @Input() meta: string = '';
    content: WritableSignal<string | null> = signal(null);

    languages = [
        ['', '<auto-detect>'],
        ['bul', 'bul - Bulgarian'],
        ['ces', 'ces - Czech'],
        ['dan', 'dan - Danish'],
        ['deu', 'deu - German'],
        ['ell', 'ell - Greek'],
        ['eng', 'eng - English'],
        ['ekk', 'ekk - Estonian'],
        ['fin', 'fin - Finnish'],
        ['fra', 'fra - French'],
        ['gle', 'gle - Irish'],
        ['hrv', 'hrv - Croatian'],
        ['hun', 'hun - Hungarian'],
        ['hye', 'hye - Armenian'],
        ['isl', 'isl - Icelandic'],
        ['ita', 'ita - Italian'],
        ['lav', 'lav - Latvian'],
        ['lit', 'lit - Lithuanian'],
        ['ltz', 'ltz - Luxembourgish'],
        ['mlt', 'mlt - Maltese'],
        ['nld', 'nld - Dutch'],
        ['nor', 'nor - Norwegian'],
        ['pol', 'pol - Polish'],
        ['por', 'por - Portuguese'],
        ['ron', 'ron - Romanian'],
        ['slk', 'slk - Slovak'],
        ['slop', 'slop - SlopScript'],
        ['slv', 'slv - Slovene'],
        ['spa', 'spa - Spanish'],
        ['sqi', 'sqi - Albanian'],
        ['srp', 'srp - Serbian'],
        ['swe', 'swe - Swedish'],
        ['ukr', 'ukr - Ukrainian'],
        // TODO extend together with Makefile
    ];

    selectedLanguage: string = '';

    constructor(public backend: Backend) {}

    run() {
        let userdata = {
            fallback_language: this.selectedLanguage,
            min_confidence: this.selectedLanguage ? 1.0 : 0.0,
        };
        this.backend.processString('Spellchecker', this.id, this.meta, userdata).subscribe({
            next: (content) => {
                this.backend.alert('Spellchecker invoked', 'success');
                this.content.set(content);
            },
            error: this.backend.defaultErrorHandler,
        });
    }
}
