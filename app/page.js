import EpisodesClient from './components/episodes-client';

function getApiBase() {
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL)
    return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  if (process.env.VERCEL_URL)
    return `https://${process.env.VERCEL_URL}`;
  return 'http://localhost:3000';
}

export const revalidate = 600;

export default async function Home() {
  const base = getApiBase();
  const opts = { next: { revalidate: 600 } };

  try {
    const [users, categories, episodes, albums] = await Promise.all([
      fetch(`${base}/api/py/users`, opts).then(r => r.json()),
      fetch(`${base}/api/py/categories`, opts).then(r => r.json()),
      fetch(`${base}/api/py/episodes?limit=12&offset=0`, opts).then(r => r.json()),
      fetch(`${base}/api/py/albums`, opts).then(r => r.json()),
    ]);

    return (
      <div className="min-h-screen bg-gray-50">
        <EpisodesClient initialData={{ users, categories, episodes, albums }} />
      </div>
    );
  } catch {
    return (
      <div className="min-h-screen bg-gray-50">
        <FallbackLoader />
      </div>
    );
  }
}

function FallbackLoader() {
  return (
    <div className="py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden animate-pulse h-[360px]">
              <div className="h-48 bg-gray-200" />
              <div className="p-4">
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4" />
                <div className="flex gap-4">
                  <div className="h-5 bg-gray-200 rounded w-12" />
                  <div className="h-5 bg-gray-200 rounded w-12" />
                  <div className="h-5 bg-gray-200 rounded w-12" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
