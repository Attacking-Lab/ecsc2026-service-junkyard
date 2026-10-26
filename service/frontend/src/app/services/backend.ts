import {Injectable, signal, WritableSignal} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {map} from 'rxjs';

export interface Response {
    ok: boolean;
    message?: string;
    filename?: string;
}

export interface UserResponse {
    username: string;
    first_name: string;
    last_name: string;
    files: string[];
}

export interface AlertMessage {
    msg: string;
    kind: string;
}

export interface MetadataResponse {
    type: "image" | "text";
    owner: string;
    first_name?: string;
    last_name?: string;
    username?: string;
    mods: string[];
}


@Injectable({
    providedIn: 'root',
})
export class Backend {

    public messages: WritableSignal<AlertMessage[]> = signal([]);

    public currentUser: WritableSignal<string | null> = signal(null);

    public alert(message: string, kind: string = 'info') {
        console.log("ALERT", message, this.messages());
        this.messages.update(msgs => [...msgs, {msg: message, kind: kind}]);
    }

    public readonly baseUrl = '/api';

    constructor(public readonly http: HttpClient) {
    }

    defaultErrorHandler = (response: any) => {
        console.error(response);
        if (response.status == 422 && response.error.detail) {
            for (let err of response.error.detail) {
                this.alert(err.msg + " " + JSON.stringify(err.loc), "danger");
            }
        } else {
            this.alert("An error occurred (status " + response.status + ")");
        }
    };

    responseHandler = (response: Response) => {
        console.log("RESPONSE", response);
        if (response.message) {
            this.alert(response.message, response.ok ? "success" : "danger");
        }
        return response;
    };

    public login(username: string, password: string) {
        return this.http.post<Response>(`${this.baseUrl}/login`, {
            username,
            password
        }).pipe(map(this.responseHandler), map(response => {
            if (response.ok) {
                this.currentUser.set(username);
            }
            return response;
        }));
    }

    public register(username: string, password: string, firstName: string, lastName: string) {
        return this.http.post<Response>(`${this.baseUrl}/register`, {
            username,
            password,
            first_name: firstName,
            last_name: lastName
        }).pipe(map(this.responseHandler), map(response => {
            if (response.ok) {
                this.currentUser.set(username);
            }
            return response;
        }));
    }

    public logout() {
        return this.http.post<Response>(`${this.baseUrl}/logout`, {}).pipe(map(this.responseHandler), map(response => {
            if (response.ok) {
                this.currentUser.set(null);
            }
            return response;
        }));
    }

    public me() {
        return this.http.get<UserResponse>(`${this.baseUrl}/me`).pipe(map(response => {
            if (response.username) {
                this.currentUser.set(response.username);
            }
            return response;
        }));
    }

    public upload(file: File) {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<Response>(`${this.baseUrl}/upload`, formData).pipe(map(this.responseHandler));
    }

    public downloadUrl(id: string, meta: string): string {
        return `${this.baseUrl}/download/${id}/${meta}`;
    }

    public metadata(id: string, meta: string) {
        return this.http.get<MetadataResponse>(`${this.baseUrl}/metadata/${id}/${meta}`);
    }

    public publish(id: string, meta: string) {
        return this.http.post<string>(`${this.baseUrl}/publish/${id}/${meta}`, {});
    }

    public process<T>(tool: string, id: string, meta: string, userdata: any = {}) {
        return this.http.post<T>(`${this.baseUrl}/process`, userdata, {
            params: {
                tool,
                filename: id,
                meta
            }
        });
    }

    public processString(tool: string, id: string, meta: string, userdata: any = {}) {
        return this.http.post(`${this.baseUrl}/process`, userdata, {
            params: {
                tool,
                filename: id,
                meta
            },
            responseType: 'text'
        });
    }

    public processBlob(tool: string, id: string, meta: string, userdata: any = {}) {
        return this.http.post(`${this.baseUrl}/process`, userdata, {
            params: {
                tool,
                filename: id,
                meta
            },
            responseType: 'blob'
        });
    }
}
