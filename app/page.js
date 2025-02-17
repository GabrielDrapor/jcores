'use client';

import EpisodesClient from './components/episodes-client';
import { useEffect, useState } from 'react';

export default function Home() {
  const [initialData, setInitialData] = useState(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [usersRes, categoriesRes, episodesRes] = await Promise.all([
          fetch('/api/py/users'),
          fetch('/api/py/categories'),
          fetch('/api/py/episodes?limit=12&offset=0')
        ]);

        const [users, categories, episodes] = await Promise.all([
          usersRes.json(),
          categoriesRes.json(),
          episodesRes.json()
        ]);

        setInitialData({ users, categories, episodes });
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };

    fetchInitialData();
  }, []);

  if (!initialData) {
    return (
      <div className="min-h-screen bg-gray-50 py-8" suppressHydrationWarning>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, index) => (
              <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden animate-pulse h-[360px]">
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

  return (
    <div className="min-h-screen bg-gray-50" suppressHydrationWarning>
      <EpisodesClient initialData={initialData} />
    </div>
  );
}
