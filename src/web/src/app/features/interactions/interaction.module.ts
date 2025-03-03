import { NgModule } from '@angular/core'; // @angular/core v16.2.0
import { CommonModule } from '@angular/common'; // @angular/common v16.2.0
import { ReactiveFormsModule } from '@angular/forms'; // @angular/forms v16.2.0
import { MatDialogModule } from '@angular/material/dialog'; // @angular/material/dialog v16.2.0
import { AgGridModule } from 'ag-grid-angular'; // ag-grid-angular v30.0.3

import { InteractionRoutingModule } from './interaction-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { FinderFiltersComponent } from './components/finder-filters/finder-filters.component';
import { FinderTableComponent } from './components/finder-table/finder-table.component';
import { InteractionDeleteModalComponent } from './components/interaction-delete-modal/interaction-delete-modal.component';
import { InteractionFormComponent } from './components/interaction-form/interaction-form.component';
import { InteractionCreatePageComponent } from './pages/interaction-create-page/interaction-create-page.component';
import { InteractionEditPageComponent } from './pages/interaction-edit-page/interaction-edit-page.component';
import { InteractionFinderPageComponent } from './pages/interaction-finder-page/interaction-finder-page.component';
import { InteractionViewPageComponent } from './pages/interaction-view-page/interaction-view-page.component';
import { InteractionService } from './services/interaction.service';
import { SearchService } from './services/search.service';
import { InteractionFormService } from './services/interaction-form.service';

/**
 * Feature module that organizes all components, services, and dependencies related to interactions
 */
@NgModule({
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    AgGridModule,
    SharedModule,
    InteractionRoutingModule
  ],
  declarations: [
    FinderFiltersComponent,
    FinderTableComponent,
    InteractionDeleteModalComponent,
    InteractionFormComponent,
    InteractionCreatePageComponent,
    InteractionEditPageComponent,
    InteractionFinderPageComponent,
    InteractionViewPageComponent
  ],
  providers: [
    InteractionService,
    SearchService,
    InteractionFormService
  ],
  exports: [
    InteractionFinderPageComponent,
    InteractionCreatePageComponent,
    InteractionEditPageComponent,
    InteractionViewPageComponent
  ]
})
export class InteractionModule {
  /**
   * Default constructor for the module
   */
  constructor() {
    // Angular creates an instance of the module
  }
}