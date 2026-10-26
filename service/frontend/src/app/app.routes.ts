import {Routes} from '@angular/router';
import {Frontpage} from './pages/frontpage/frontpage';
import {User} from './pages/user/user';
import {Junk} from './pages/junk/junk';

export const routes: Routes = [
    {path: '', component: Frontpage},
    {path: 'user', component: User},
    {path: 'junk/:id', component: Junk},
    {path: 'junk/:id/:meta', component: Junk},
];
