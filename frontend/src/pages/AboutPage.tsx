import { Link } from 'react-router-dom'
import ImageWithFallback from '../components/ImageWithFallback'
import { aboutContent } from '../content/about'
import { splitCommaList, useHospitalInfo } from '../lib/useHospitalInfo'

function Chip({ children }: { children: string }) {
  return (
    <span className="rounded-full bg-cream px-3 py-1 text-sm font-medium text-primary">
      {children}
    </span>
  )
}

export default function AboutPage() {
  const hospital = useHospitalInfo()
  const departments = hospital.status === 'success' ? splitCommaList(hospital.data.departments) : []
  const facilities = hospital.status === 'success' ? splitCommaList(hospital.data.facilities) : []

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      {/* Hero */}
      <section className="text-center">
        <ImageWithFallback
          src="/images/about-hero.jpg"
          alt="Welcoming hospital exterior and reception"
          className="mx-auto h-56 w-full max-w-3xl rounded-2xl object-cover"
        />
        <h1 className="mt-6 text-3xl font-bold text-primary">{aboutContent.heroTitle}</h1>
        <p className="mt-2 text-primary/70">{aboutContent.heroSubtitle}</p>
      </section>

      {/* Intro */}
      <section className="mt-10">
        <p className="text-primary/80">{aboutContent.intro}</p>
      </section>

      {/* Mission */}
      <section className="mt-10 grid items-center gap-6 md:grid-cols-2">
        <ImageWithFallback
          src="/images/about-care.jpg"
          alt="A doctor caring for a patient"
          className="h-48 w-full rounded-2xl object-cover"
        />
        <div>
          <h2 className="text-xl font-bold text-primary">{aboutContent.mission.title}</h2>
          <p className="mt-2 text-primary/80">{aboutContent.mission.text}</p>
        </div>
      </section>

      {/* Values */}
      <section className="mt-10">
        <h2 className="text-xl font-bold text-primary">Our values</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          {aboutContent.values.map((value) => (
            <div key={value.title} className="rounded-2xl bg-cream p-5">
              <h3 className="font-semibold text-primary">{value.title}</h3>
              <p className="mt-1 text-sm text-primary/70">{value.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why choose us */}
      <section className="mt-10">
        <h2 className="text-xl font-bold text-primary">Why choose us</h2>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-primary/80">
          {aboutContent.whyChooseUs.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </section>

      {/* Departments + facilities (live) */}
      <section className="mt-10">
        <h2 className="text-xl font-bold text-primary">Departments</h2>
        {hospital.status === 'loading' && <p className="mt-2 text-primary/60">Loading...</p>}
        {hospital.status === 'error' && (
          <p className="mt-2 text-primary/60">Couldn't load live department data right now.</p>
        )}
        {departments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {departments.map((dept) => (
              <Chip key={dept}>{dept}</Chip>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-primary">Facilities</h2>
        {facilities.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {facilities.map((facility) => (
              <Chip key={facility}>{facility}</Chip>
            ))}
          </div>
        )}
        <ImageWithFallback
          src="/images/about-facility.jpg"
          alt="A hospital facility such as a ward or laboratory"
          className="mt-6 h-48 w-full rounded-2xl object-cover"
        />
      </section>

      <div className="mt-12 text-center">
        <Link
          to="/"
          className="inline-block rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white"
        >
          Chat with Celia
        </Link>
      </div>
    </div>
  )
}
