import {
    Component,
    computed,
    inject,
    OnInit,
    signal,
    Signal,
    WritableSignal,
    ChangeDetectionStrategy,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, EMPTY } from 'rxjs';
import { ToolInspector } from '../../components/tool-inspector/tool-inspector';
import { ToolCropper } from '../../components/tool-cropper/tool-cropper';
import { ToolCensor } from '../../components/tool-censor/tool-censor';
import { Backend, MetadataResponse } from '../../services/backend';
import { ToolReader } from '../../components/tool-reader/tool-reader';
import { ToolSpellchecker } from '../../components/tool-spellchecker/tool-spellchecker';
import { rxResource } from '@angular/core/rxjs-interop';
import { ToolConverterI2t } from '../../components/tool-converter-i2t/tool-converter-i2t';
import { ToolConverterT2i } from '../../components/tool-converter-t2i/tool-converter-t2i';

@Component({
    selector: 'app-junk',
    imports: [
        ToolInspector,
        ToolCropper,
        ToolCensor,
        ToolReader,
        ToolSpellchecker,
        ToolConverterI2t,
        ToolConverterT2i,
    ],
    templateUrl: './junk.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './junk.scss',
})
export class Junk {
    private route = inject(ActivatedRoute);

    id: WritableSignal<string> = signal('');
    meta: WritableSignal<string> = signal('base');
    loadedMeta = rxResource({
        params: computed(() => {
            return { meta: this.meta(), id: this.id() };
        }),
        stream: ({ params: { id, meta } }) => {
            return this.backend.metadata(id, meta).pipe(
                catchError((error) => {
                    this.backend.defaultErrorHandler(error);
                    return EMPTY;
                }),
            );
        },
    });
    tools = computed(() => this.updateTools());
    currentTool: string = '';

    constructor(
        private backend: Backend,
        private router: Router,
    ) {
        this.route.params.subscribe((params) => {
            this.id.set(params['id']);
            this.meta.set(params['meta'] || 'base');
        });
        this.id.set(this.route.snapshot.paramMap.get('id') || '');
        this.meta.set(this.route.snapshot.paramMap.get('meta') || 'base');
    }

    updateTools(): string[] {
        let tools: string[] = [];
        if (this.loadedMeta.value()?.type == 'image') {
            tools = ['Scanner', 'Slicer', 'Redactor', 'Converter (i2t)'];
        }
        if (this.loadedMeta.value()?.type == 'text') {
            tools = ['Microscope', 'Chromatograph', 'Converter (t2i)'];
        }
        if (!this.loadedMeta.value()?.mods.includes('published')) {
            tools.push('Publish');
        }
        if (!tools.includes(this.currentTool)) {
            if (tools.length > 0) {
                this.currentTool = tools[0];
            } else {
                this.currentTool = '';
            }
        }
        return tools;
    }

    publish() {
        this.backend.publish(this.id(), this.meta()).subscribe({
            next: (newMeta) => {
                this.backend.alert('Junk published, others may use it', 'success');
                this.router.navigate(['/junk', this.id(), newMeta]);
            },
            error: this.backend.defaultErrorHandler,
        });
    }
}
