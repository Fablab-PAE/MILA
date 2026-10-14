import { HttpClient, HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { App } from './app';
import { inject, Injectable } from '@angular/core';
import { HttpTestingController } from '@angular/common/http/testing';

@Injectable({ providedIn: 'root' })
class MilaService {
  private http = inject(HttpClient);
  start() {
    return this.http.get('/mila/start', { responseType: 'text' });
  }
  stop() {
    return this.http.get('/mila/stop', { responseType: 'text' });
  }
}

describe('App', () => {
  let service: MilaService;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    service = TestBed.inject(MilaService);
    http = TestBed.inject(HttpTestingController);
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Mila');
  });

  afterEach(() => http.verify()); // échoue si une requête n'a pas été traitée

  it('start renvoie "Mila is On"', () => {
    let result: string | undefined;
    service.start().subscribe((r) => (result = r));

    const req = http.expectOne('/mila/start');
    expect(req.request.method).toBe('GET');
    req.flush('Mila is On');

    expect(result).toBe('Mila is On');
  });

  it('stop renvoie "Mila is Off"', () => {
    let result: string | undefined;
    service.stop().subscribe((r) => (result = r));

    http.expectOne('/mila/stop').flush('Mila is Off');

    expect(result).toBe('Mila is Off');
  });

  it('start échoue avec "Erreur"', () => {
    let error: HttpErrorResponse | undefined;
    service.start().subscribe({ error: (e) => (error = e) });

    http.expectOne('/mila/start').flush('Erreur', { status: 500, statusText: 'Server Error' });

    expect(error?.status).toBe(500);
    expect(error?.error).toBe('Erreur');
  });
});
