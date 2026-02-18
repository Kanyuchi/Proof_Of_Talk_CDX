import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const initialProfile = {
  full_name: '',
  email: '',
  password: '',
  title: '',
  organization: '',
  role: 'attendee',
  website: '',
  linkedin: '',
  bio: ''
}

export default function AuthPage() {
  const { user, login, register, updateProfile } = useAuth()
  const [registerForm, setRegisterForm] = useState(initialProfile)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    title: user?.title || '',
    organization: user?.organization || '',
    role: user?.role || 'attendee',
    website: '',
    linkedin: '',
    bio: ''
  })
  const [message, setMessage] = useState('')

  async function onRegister(e) {
    e.preventDefault()
    try {
      await register({
        full_name: registerForm.full_name,
        email: registerForm.email,
        password: registerForm.password,
        title: registerForm.title,
        organization: registerForm.organization,
        role: registerForm.role,
        website: registerForm.website,
        bio: registerForm.bio,
        social_links: { linkedin: registerForm.linkedin },
        focus: [],
        looking_for: []
      })
      setMessage('Account created and signed in.')
    } catch (err) {
      setMessage(err.message)
    }
  }

  async function onLogin(e) {
    e.preventDefault()
    try {
      await login(loginForm.email, loginForm.password)
      setMessage('Signed in successfully.')
    } catch (err) {
      setMessage(err.message)
    }
  }

  async function onProfileSave(e) {
    e.preventDefault()
    try {
      await updateProfile({
        full_name: profileForm.full_name,
        title: profileForm.title,
        organization: profileForm.organization,
        role: profileForm.role,
        website: profileForm.website,
        bio: profileForm.bio,
        social_links: { linkedin: profileForm.linkedin },
        focus: [],
        looking_for: []
      })
      setMessage('Profile updated.')
    } catch (err) {
      setMessage(err.message)
    }
  }

  return (
    <section className="grid two-cols">
      <article className="panel">
        <h2>Create account</h2>
        <form className="form" onSubmit={onRegister}>
          <input placeholder="Full name" value={registerForm.full_name} onChange={(e) => setRegisterForm((p) => ({ ...p, full_name: e.target.value }))} required />
          <input placeholder="Email" type="email" value={registerForm.email} onChange={(e) => setRegisterForm((p) => ({ ...p, email: e.target.value }))} required />
          <input placeholder="Password" type="password" value={registerForm.password} onChange={(e) => setRegisterForm((p) => ({ ...p, password: e.target.value }))} required />
          <input placeholder="Title" value={registerForm.title} onChange={(e) => setRegisterForm((p) => ({ ...p, title: e.target.value }))} />
          <input placeholder="Organization" value={registerForm.organization} onChange={(e) => setRegisterForm((p) => ({ ...p, organization: e.target.value }))} />
          <select value={registerForm.role} onChange={(e) => setRegisterForm((p) => ({ ...p, role: e.target.value }))}>
            <option value="attendee">Attendee</option>
            <option value="vip">VIP</option>
            <option value="speaker">Speaker</option>
            <option value="sponsor">Sponsor</option>
            <option value="delegate">Delegate</option>
          </select>
          <input placeholder="Website" value={registerForm.website} onChange={(e) => setRegisterForm((p) => ({ ...p, website: e.target.value }))} />
          <input placeholder="LinkedIn" value={registerForm.linkedin} onChange={(e) => setRegisterForm((p) => ({ ...p, linkedin: e.target.value }))} />
          <textarea placeholder="Bio" value={registerForm.bio} onChange={(e) => setRegisterForm((p) => ({ ...p, bio: e.target.value }))} />
          <button className="btn primary" type="submit">Register</button>
        </form>
      </article>

      <article className="panel">
        <h2>Sign in</h2>
        <form className="form" onSubmit={onLogin}>
          <input placeholder="Email" type="email" value={loginForm.email} onChange={(e) => setLoginForm((p) => ({ ...p, email: e.target.value }))} required />
          <input placeholder="Password" type="password" value={loginForm.password} onChange={(e) => setLoginForm((p) => ({ ...p, password: e.target.value }))} required />
          <button className="btn primary" type="submit">Login</button>
        </form>

        <hr />
        <h2>Profile</h2>
        <form className="form" onSubmit={onProfileSave}>
          <input placeholder="Full name" value={profileForm.full_name} onChange={(e) => setProfileForm((p) => ({ ...p, full_name: e.target.value }))} />
          <input placeholder="Title" value={profileForm.title} onChange={(e) => setProfileForm((p) => ({ ...p, title: e.target.value }))} />
          <input placeholder="Organization" value={profileForm.organization} onChange={(e) => setProfileForm((p) => ({ ...p, organization: e.target.value }))} />
          <select value={profileForm.role} onChange={(e) => setProfileForm((p) => ({ ...p, role: e.target.value }))}>
            <option value="attendee">Attendee</option>
            <option value="vip">VIP</option>
            <option value="speaker">Speaker</option>
            <option value="sponsor">Sponsor</option>
            <option value="delegate">Delegate</option>
          </select>
          <input placeholder="Website" value={profileForm.website} onChange={(e) => setProfileForm((p) => ({ ...p, website: e.target.value }))} />
          <input placeholder="LinkedIn" value={profileForm.linkedin} onChange={(e) => setProfileForm((p) => ({ ...p, linkedin: e.target.value }))} />
          <textarea placeholder="Bio" value={profileForm.bio} onChange={(e) => setProfileForm((p) => ({ ...p, bio: e.target.value }))} />
          <button className="btn ghost" type="submit">Save profile</button>
        </form>
        {!!message && <p className="muted">{message}</p>}
      </article>
    </section>
  )
}
