import { Component, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { RouterOutlet } from '@angular/router';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  constructor(private http: HttpClient) {}
  protected readonly title = signal('Mila');
  protected readonly status = signal('Mila is OFF');

  startMila() {
    this.http.get(`http://${environment.raspberryPiHost}:3000/mila/start`).subscribe({
      next: (response) => {
        console.log('Mila started successfully', response);
        this.status.set('Mila is ON');
      },
      error: (error) => {
          console.error('Error starting Mila', error);
          this.status.set('Error starting Mila');
      },
    });
  }

  stopMila() {
    this.http.get(`http://${environment.raspberryPiHost}:3000/mila/stop`).subscribe({
      next: (response) => {
        console.log('Mila stopped successfully', response);
        this.status.set('Mila is OFF');
      },
      error: (error) => {
        console.error('Error stopping Mila', error);
        this.status.set('Error stopping Mila');
      },
    });
  }
}
