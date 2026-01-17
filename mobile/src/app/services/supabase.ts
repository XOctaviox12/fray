import { Injectable } from '@angular/core';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SupabaseService {
  private supabase: SupabaseClient;

  constructor() {
    this.supabase = createClient(environment.supabaseUrl, environment.supabaseKey);
  }

  // Ejemplo: Obtener perfil del usuario actual
  get user() {
    return this.supabase.auth.getUser();
  }

  // Aquí la Persona 4 programará el "Vigilante" (Realtime)
  get authChanges() {
    return this.supabase.auth.onAuthStateChange;
  }
}
