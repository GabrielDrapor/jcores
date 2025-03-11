'use client';

import { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const SortingSection = ({ sortField, sortOrder, onSortChange, selectedAlbumId }) => {
  const options = [
    { value: 'published_at', label: '发布时间' },
    { value: 'likes_count', label: '点赞数' },
  ];

  return (
    <div className="flex items-center gap-2 justify-between w-full">
      <div className="flex items-center gap-2">
        <div className="flex rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => onSortChange(option.value, option.value === sortField ? !sortOrder : true)}
              className={`px-4 py-2 text-sm font-medium ${option.value === sortField
                ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                : 'text-gray-700 hover:bg-gray-50'
                } focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500/20 transition-colors border-r border-gray-200 last:border-r-0`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => onSortChange(sortField, !sortOrder)}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500/20 transition-colors bg-white shadow-sm"
        >
          <svg className={`w-4 h-4 transition-transform duration-200 ${!sortOrder ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span className="whitespace-nowrap">{!sortOrder ? '升序' : '降序'}</span>
        </button>
      </div>
      {selectedAlbumId && (
        <a
          href={`gcores://open?url=${encodeURIComponent(`https://www.gcores.com/albums/${selectedAlbumId}`)}`}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg border border-blue-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500/20 transition-colors bg-white shadow-sm"
        >
          <span className="whitespace-nowrap">查看播单</span>
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
          </svg>
        </a>
      )}
    </div>
  );
};

const AlbumList = ({ albums, selectedAlbumId, onAlbumSelect }) => {
  return (
    <div className="mb-6 pb-6 border-b border-gray-100">
      <div className="flex flex-wrap gap-3">
        {albums.map((album) => (
          <button
            key={album.id}
            onClick={() => onAlbumSelect(album.id)}
            className={`group flex items-center gap-3 pl-2 pr-5 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all transform hover:scale-[1.02] active:scale-[0.98] ${selectedAlbumId === album.id
                ? 'bg-blue-50 text-blue-700 ring-2 ring-blue-500/20 hover:bg-blue-100 shadow-sm hover:shadow'
                : 'bg-gray-50/80 text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
          >
            <div className={`w-12 h-12 rounded-lg overflow-hidden ring-2 transition-all ${selectedAlbumId === album.id
                ? 'ring-blue-500 ring-offset-2'
                : 'ring-gray-200 group-hover:ring-gray-300 group-hover:ring-offset-1'
              }`}
            >
              {album.cover ? (
                <img
                  src={`/api/py/image-proxy/${album.cover}`}
                  alt={album.title}
                  className="w-full h-full object-cover transition-transform group-hover:scale-110"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500 text-base font-medium">
                  {album.title.slice(0, 2)}
                </div>
              )}
            </div>
            <span className="transition-colors">{album.title}</span>
            {selectedAlbumId === album.id && (
              <div className="w-2 h-2 rounded-full bg-blue-500 ml-2" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

const FilterSection = ({ users, categories, albums, selectedUserId, selectedCategoryId, selectedAlbumId, onUserSelect, onCategorySelect, onAlbumSelect, sortField, sortOrder, onSortChange }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
      <div className="flex justify-center mb-4">
        <img
          src="/logo.webp"
          alt="Logo"
          className="h-24 w-auto"
          suppressHydrationWarning
        />
      </div>
      <UserList users={users} selectedUserId={selectedUserId} onUserSelect={onUserSelect} />
      <CategoryList categories={categories} selectedCategoryId={selectedCategoryId} onCategorySelect={onCategorySelect} />
      <div className="mt-6 pt-6 border-t border-gray-100">
        <AlbumList albums={albums} selectedAlbumId={selectedAlbumId} onAlbumSelect={onAlbumSelect} />
      </div>
      <div className="mt-6 pt-6 border-t border-gray-100">
        <SortingSection sortField={sortField} sortOrder={sortOrder} onSortChange={onSortChange} selectedAlbumId={selectedAlbumId} />
      </div>
    </div>
  );
};

const UserList = ({ users, selectedUserId, onUserSelect }) => {
  return (
    <div className="mb-6 pb-6 border-b border-gray-100">
      <div className="flex flex-wrap gap-3">
        {users.map((user) => (
          <button
            key={user.id}
            onClick={() => onUserSelect(user.id)}
            className={`group flex items-center gap-3 pl-2 pr-5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all transform hover:scale-[1.02] active:scale-[0.98] ${selectedUserId === user.id
              ? 'bg-blue-50 text-blue-700 ring-2 ring-blue-500/20 hover:bg-blue-100 shadow-sm hover:shadow'
              : 'bg-gray-50/80 text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
          >
            <div className={`w-10 h-10 rounded-full overflow-hidden ring-2 transition-all ${selectedUserId === user.id
              ? 'ring-blue-500 ring-offset-2'
              : 'ring-gray-200 group-hover:ring-gray-300 group-hover:ring-offset-1'}`}
            >
              {user.thumb ? (
                <img
                  src={`/api/py/image-proxy/${user.thumb}`}
                  alt={user.nickname}
                  className="w-full h-full object-cover transition-transform group-hover:scale-110"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500 text-lg font-medium">
                  {user.nickname.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            <span className="transition-colors">{user.nickname}</span>
            {selectedUserId === user.id && (
              <div className="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center ml-1">
                <svg className="w-3 h-3 text-blue-600" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 4l-8 8" />
                  <path d="M4 4l8 8" />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

const CategoryList = ({ categories, selectedCategoryId, onCategorySelect }) => {
  // Function to generate a random gradient
  const getRandomGradient = (id) => {
    // Use category id to keep the gradient consistent for each category
    const gradients = [
      'from-purple-100 to-pink-200',
      'from-cyan-100 to-blue-200',
      'from-green-100 to-emerald-200',
      'from-orange-100 to-red-200',
      'from-pink-100 to-rose-200',
      'from-indigo-100 to-violet-200',
      'from-yellow-100 to-orange-200',
      'from-blue-100 to-indigo-200',
      'from-red-100 to-rose-200',
      'from-teal-100 to-cyan-200',
    ];
    return gradients[id % gradients.length];
  };
  return (
    <div className="mb-6">
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => onCategorySelect(category.id)}
            className={`px-4 py-2 text-base font-mono font-bold tracking-tight whitespace-nowrap transition-all
              ${selectedCategoryId === category.id
                ? `bg-gradient-to-r ${getRandomGradient(category.id)} text-gray-800 shadow-lg shadow-current/20 hover:shadow-current/30 hover:-translate-y-0.5 saturate-[1.2]`
                : `bg-gradient-to-r ${getRandomGradient(category.id)} text-gray-600 hover:text-gray-800 opacity-90 hover:opacity-100 saturate-[0.9] hover:saturate-[1.2]`}
              rounded-md border border-black/5 backdrop-blur-sm
              transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-150
              hover:border-black/10 focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
          >
            <span className="relative">
              {category.name}
              {selectedCategoryId === category.id && (
                <span className="absolute -right-3 top-0.5 flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-200 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-400"></span>
                </span>
              )}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

const EpisodeCardSkeleton = () => {
  return (
    <article className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden animate-pulse h-[360px] flex flex-col">
      <div className="h-48 bg-gray-200" />
      <div className="p-4 flex-1 flex flex-col">
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2 flex-shrink-0" />
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-4 flex-shrink-0" />
        <div className="flex flex-wrap gap-4 mt-auto">
          <div className="h-5 bg-gray-200 rounded w-12" />
          <div className="h-5 bg-gray-200 rounded w-12" />
          <div className="h-5 bg-gray-200 rounded w-12" />
        </div>
      </div>
    </article>
  );
};

const EpisodeCard = ({ episode }) => {
  return (
    <a
      href={`gcores://open?url=${encodeURIComponent(`https://gcores.com/radios/${episode.id}`)}`}
      className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow h-[360px] flex flex-col no-underline"
      suppressHydrationWarning>

      <div className="relative h-48 bg-gray-100 overflow-hidden">
        {episode.thumb && (
          <img
            src={`/api/py/image-proxy/${episode.thumb}`}
            alt={episode.title}
            className="absolute inset-0 w-full h-full object-cover object-center"
          />
        )}
      </div>
      <div className="p-4 flex-1 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 flex-shrink-0">
          {episode.title}
        </h3>
        <div className="text-sm text-gray-500 mt-auto">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
              </svg>
              <span>{episode.likes_count || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
              </svg>
              <span>{episode.bookmarks_count || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              <span>{episode.comments_count || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </a>
  );
};

export default function EpisodesClient({ initialData }) {
  const [episodes, setEpisodes] = useState(initialData.episodes);
  const [users, setUsers] = useState(initialData.users);
  const [categories, setCategories] = useState(initialData.categories);
  const [albums, setAlbums] = useState(initialData.albums);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);
  const [categoryId, setCategoryId] = useState(null);
  const [albumId, setAlbumId] = useState(null);
  const [sortField, setSortField] = useState('published_at');
  const [sortOrder, setSortOrder] = useState(true);
  const [offset, setOffset] = useState(12);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const observerTarget = useRef(null);

  const fetchEpisodes = async (isLoadingMore = false, customParams = null) => {
    if (!isLoadingMore) {
      setLoading(true);
      setOffset(0);
    } else {
      setLoadingMore(true);
    }

    try {
      let params;
      if (customParams) {
        params = customParams;
      } else {
        params = new URLSearchParams();
        if (userId) params.append('user_id', userId.toString());
        if (categoryId) params.append('category_id', categoryId.toString());
        if (albumId) params.append('album_id', albumId.toString());
        if (sortField) {
          params.append('sort_field_str', sortField);
          params.append('asc', (!sortOrder).toString());  // Only send asc when sort field is selected
        }
        params.append('limit', '12');
        params.append('offset', isLoadingMore ? offset.toString() : '0');
      }

      const response = await axios.get(`/api/py/episodes?${params.toString()}`);
      const newEpisodes = response.data;

      if (newEpisodes.length < 12) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }

      // Deduplicate episodes based on their ID
      const uniqueEpisodes = isLoadingMore
        ? [...new Map([...episodes, ...newEpisodes].map(episode => [episode.id, episode])).values()]
        : newEpisodes;

      if (isLoadingMore) {
        setEpisodes(uniqueEpisodes);
        setOffset(prev => prev + newEpisodes.length);
      } else {
        setEpisodes(newEpisodes);
        setOffset(newEpisodes.length);
      }
    } catch (error) {
      console.error('Error fetching episodes:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          fetchEpisodes(true);
        }
      },
      { threshold: 1.0 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => {
      if (observerTarget.current) {
        observer.unobserve(observerTarget.current);
      }
    };
  }, [hasMore, loadingMore, loading, offset]);

  return (
    <div className="min-h-screen bg-gray-50 py-8" suppressHydrationWarning>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FilterSection
          users={users}
          categories={categories}
          albums={albums}
          selectedUserId={userId}
          selectedCategoryId={categoryId}
          selectedAlbumId={albumId}
          sortField={sortField}
          sortOrder={sortOrder}
          onUserSelect={(id) => {
            const newUserId = id === userId ? null : id;
            setUserId(newUserId);
            const params = new URLSearchParams();
            if (newUserId) params.append('user_id', newUserId.toString());
            if (categoryId) params.append('category_id', categoryId.toString());
            if (albumId) params.append('album_id', albumId.toString());
            if (sortField) {
              params.append('sort_field_str', sortField);
              params.append('asc', (!sortOrder).toString());
            }
            params.append('limit', '12');
            params.append('offset', '0');
            fetchEpisodes(false, params);
          }}
          onCategorySelect={(id) => {
            const newCategoryId = id === categoryId ? null : id;
            setCategoryId(newCategoryId);
            const params = new URLSearchParams();
            if (userId) params.append('user_id', userId.toString());
            if (newCategoryId) params.append('category_id', newCategoryId.toString());
            if (albumId) params.append('album_id', albumId.toString());
            if (sortField) {
              params.append('sort_field_str', sortField);
              params.append('asc', (!sortOrder).toString());
            }
            params.append('limit', '12');
            params.append('offset', '0');
            fetchEpisodes(false, params);
          }}
          onSortChange={(field, order) => {
            const newSortField = field || null;
            setSortField(newSortField);
            setSortOrder(order);
            const params = new URLSearchParams();
            if (userId) params.append('user_id', userId.toString());
            if (categoryId) params.append('category_id', categoryId.toString());
            if (albumId) params.append('album_id', albumId.toString());
            if (newSortField) {
              params.append('sort_field_str', newSortField);
              params.append('asc', (!order).toString());
            }
            params.append('limit', '12');
            params.append('offset', '0');
            fetchEpisodes(false, params);
          }}
          onAlbumSelect={(id) => {
            const newAlbumId = id === albumId ? null : id;
            setAlbumId(newAlbumId);
            const params = new URLSearchParams();
            if (userId) params.append('user_id', userId.toString());
            if (categoryId) params.append('category_id', categoryId.toString());
            if (newAlbumId) params.append('album_id', newAlbumId.toString());
            if (sortField) {
              params.append('sort_field_str', sortField);
              params.append('asc', (!sortOrder).toString());
            }
            params.append('limit', '12');
            params.append('offset', '0');
            fetchEpisodes(false, params);
          }}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            // Show 6 skeleton cards during loading
            [...Array(6)].map((_, index) => (
              <EpisodeCardSkeleton key={index} />
            ))
          ) : (
            <>
              {episodes.map((episode) => (
                <EpisodeCard key={episode.id} episode={episode} />
              ))}
              {loadingMore && (
                <div className="col-span-full flex justify-center py-4">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </>
          )}
        </div>

        {!loading && !loadingMore && hasMore && (
          <div ref={observerTarget} className="h-4" />
        )}
      </div>
    </div>
  );
}
