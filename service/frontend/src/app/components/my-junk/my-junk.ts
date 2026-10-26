import { ChangeDetectorRef, Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { Backend } from '../../services/backend';
import { RouterLink } from '@angular/router';

@Component({
    selector: 'app-my-junk',
    imports: [RouterLink],
    templateUrl: './my-junk.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './my-junk.scss',
})
export class MyJunk {
    @Input() files: string[] = [];

    uploads: number = 0;

    constructor(
        public backend: Backend,
        public cd: ChangeDetectorRef,
    ) {}

    protected onFileDrop($event: DragEvent) {
        $event.preventDefault();
        $event.stopPropagation();
        this.upload($event.dataTransfer!.files);
    }

    protected onFileSelect($event: Event) {
        $event.preventDefault();
        $event.stopPropagation();
        this.upload(($event.target as any).files);
    }

    protected upload(files: FileList) {
        for (let f of files) {
            console.log(f);
            this.uploads++;
            this.backend.upload(f).subscribe({
                next: (response) => {
                    if (response.ok) {
                        this.backend.alert(`Uploaded junk ${response.filename}`);
                        this.uploads--;
                        this.files.push(response.filename!);
                        this.cd.markForCheck();
                    }
                },
                error: this.backend.defaultErrorHandler,
            });
        }
    }
}
