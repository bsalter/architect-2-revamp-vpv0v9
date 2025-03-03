import { NgModule, ErrorHandler } from '@angular/core'; // @angular/core 16.2.0
import { BrowserModule } from '@angular/platform-browser'; // @angular/platform-browser 16.2.0
import { BrowserAnimationsModule } from '@angular/platform-browser/animations'; // @angular/platform-browser/animations 16.2.0
import { HttpClientModule } from '@angular/common/http'; // @angular/common/http 16.2.0

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CoreModule } from './core/core.module';
import { SharedModule } from './shared/shared.module';
import { environment } from '../environments/environment';

/**
 * Root Angular module that bootstraps the application and configures necessary dependencies
 */
@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    CoreModule.forRoot(),
    SharedModule,
    AppRoutingModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {
  /**
   * Default constructor for AppModule
   */
  constructor() { }
}