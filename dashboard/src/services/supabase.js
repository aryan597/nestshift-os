import { createClient } from '@supabase/supabase-js'

// These will be overridden at runtime via OS environment injection
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || ''
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// Hub registration - called after successful user login
export const registerHub = async (userId) => {
  const hubId = window.hardwareId || crypto.randomUUID()

  const { data, error } = await supabase
    .from('hubs')
    .upsert({
      id: hubId,
      user_id: userId,
      ip_address: window.location.hostname,
      last_seen: new Date().toISOString(),
      version: import.meta.env.VITE_APP_VERSION || '1.0.0'
    })
    .select()

  return { data, error, hubId }
}
