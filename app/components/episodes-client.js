'use client';

import { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const SortingSection = ({ sortField, sortOrder, onSortChange }) => {
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
    </div>
  );
};

const SearchInput = ({ value, onChange, placeholder }) => (
  <div className="relative mb-3">
    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
    </svg>
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 transition-colors"
    />
    {value && (
      <button onClick={() => onChange('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M12 4l-8 8" /><path d="M4 4l8 8" />
        </svg>
      </button>
    )}
  </div>
);


const TABS = [
  { key: 'users', label: '主播' },
  { key: 'categories', label: '分类' },
  { key: 'albums', label: '播单' },
];
const TOP_USERS = 12;
const TOP_ALBUMS = 9;

const FilterSection = ({ users, categories, albums, selectedUserIds, selectedCategoryId, selectedAlbumId, onUserSelect, onCategorySelect, onAlbumSelect, sortField, sortOrder, onSortChange }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [query, setQuery] = useState('');

  const activeCount = selectedUserIds.length + (selectedCategoryId ? 1 : 0) + (selectedAlbumId ? 1 : 0);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setQuery('');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
      <div className="flex justify-center mb-5">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Gadio Dig</h1>
      </div>

      {activeCount > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-4 pb-4 border-b border-gray-100">
          <span className="text-xs text-gray-400 mr-1">筛选中</span>
          {selectedUserIds.map(uid => {
            const u = users.find(u => u.id === uid);
            return u ? (
              <button key={uid} onClick={() => onUserSelect(uid)} className="flex items-center gap-1.5 pl-1.5 pr-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium hover:bg-blue-100 transition-colors">
                <div className="w-5 h-5 rounded-full overflow-hidden ring-1 ring-blue-300">
                  {u.thumb ? <img src={`/api/py/image-proxy/${u.thumb}`} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full bg-blue-200" />}
                </div>
                {u.nickname}
                <svg className="w-3 h-3 text-blue-400" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 4l-8 8M4 4l8 8" /></svg>
              </button>
            ) : null;
          })}
          {selectedCategoryId && (() => {
            const c = categories.find(c => c.id === selectedCategoryId);
            return c ? (
              <button onClick={() => onCategorySelect(selectedCategoryId)} className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium hover:bg-blue-100 transition-colors">
                {c.name}
                <svg className="w-3 h-3 text-blue-400" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 4l-8 8M4 4l8 8" /></svg>
              </button>
            ) : null;
          })()}
          {selectedAlbumId && (() => {
            const a = albums.find(a => a.id === selectedAlbumId);
            return a ? (
              <button onClick={() => onAlbumSelect(selectedAlbumId)} className="flex items-center gap-1.5 pl-1.5 pr-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium hover:bg-blue-100 transition-colors">
                <div className="w-5 h-5 rounded-lg overflow-hidden ring-1 ring-blue-300">
                  {a.cover ? <img src={`/api/py/image-proxy/${a.cover}`} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full bg-blue-200" />}
                </div>
                {a.title}
                <svg className="w-3 h-3 text-blue-400" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 4l-8 8M4 4l8 8" /></svg>
              </button>
            ) : null;
          })()}
        </div>
      )}

      <div className="flex gap-1 mb-4">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === tab.key
              ? 'bg-gray-900 text-white'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}
          >
            {tab.label}
            <span className="ml-1.5 text-xs opacity-60">
              {tab.key === 'users' ? users.length : tab.key === 'categories' ? categories.length : albums.length}
            </span>
          </button>
        ))}
      </div>

      {activeTab === 'users' && (
        <>
          <SearchInput value={query} onChange={setQuery} placeholder={`搜索主播...`} />
          <div className="flex flex-wrap gap-2">
            {(() => {
              const filtered = query.trim() ? users.filter(u => u.nickname.toLowerCase().includes(query.trim().toLowerCase())) : users.slice(0, TOP_USERS);
              return filtered.length > 0 ? filtered.map(user => {
                const selected = selectedUserIds.includes(user.id);
                return (
                <button key={user.id} onClick={() => onUserSelect(user.id)}
                  className={`group flex items-center gap-2 pl-1.5 pr-3.5 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all hover:scale-[1.02] active:scale-[0.98] ${selected
                    ? 'bg-blue-50 text-blue-700 ring-2 ring-blue-500/20 shadow-sm'
                    : 'bg-gray-50/80 text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}>
                  <div className={`w-8 h-8 rounded-full overflow-hidden ring-1.5 ${selected ? 'ring-blue-500' : 'ring-gray-200'}`}>
                    {user.thumb ? <img src={`/api/py/image-proxy/${user.thumb}`} alt={user.nickname} className="w-full h-full object-cover" />
                      : <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500 text-xs">{user.nickname.charAt(0)}</div>}
                  </div>
                  <span>{user.nickname}</span>
                </button>
              );}) : <span className="text-sm text-gray-400 py-2">未找到匹配的主播</span>;
            })()}
          </div>
        </>
      )}

      {activeTab === 'categories' && (
        <>
          <SearchInput value={query} onChange={setQuery} placeholder={`搜索分类...`} />
          <div className="flex flex-wrap gap-2">
            {(() => {
              const filtered = query.trim() ? categories.filter(c => c.name.toLowerCase().includes(query.trim().toLowerCase())) : categories;
              return filtered.length > 0 ? filtered.map(cat => (
                <button key={cat.id} onClick={() => onCategorySelect(cat.id)}
                  className={`px-3 py-1.5 text-sm whitespace-nowrap rounded-md transition-colors ${selectedCategoryId === cat.id
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900'}`}>
                  {cat.name}
                </button>
              )) : <span className="text-sm text-gray-400 py-2">未找到匹配的分类</span>;
            })()}
          </div>
        </>
      )}

      {activeTab === 'albums' && (
        <>
          <SearchInput value={query} onChange={setQuery} placeholder={`搜索播单...`} />
          <div className="flex flex-wrap gap-2">
            {(() => {
              const filtered = query.trim() ? albums.filter(a => a.title.toLowerCase().includes(query.trim().toLowerCase())) : albums.slice(0, TOP_ALBUMS);
              return filtered.length > 0 ? filtered.map(album => (
                <button key={album.id} onClick={() => onAlbumSelect(album.id)}
                  className={`group flex items-center gap-2 pl-1.5 pr-3.5 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all hover:scale-[1.02] active:scale-[0.98] ${selectedAlbumId === album.id
                    ? 'bg-blue-50 text-blue-700 ring-2 ring-blue-500/20 shadow-sm'
                    : 'bg-gray-50/80 text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}>
                  <div className={`w-10 h-10 rounded-md overflow-hidden ring-1.5 ${selectedAlbumId === album.id ? 'ring-blue-500' : 'ring-gray-200'}`}>
                    {album.cover ? <img src={`/api/py/image-proxy/${album.cover}`} alt={album.title} className="w-full h-full object-cover" />
                      : <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500 text-xs">{album.title.slice(0, 2)}</div>}
                  </div>
                  <span>{album.title}</span>
                </button>
              )) : <span className="text-sm text-gray-400 py-2">未找到匹配的播单</span>;
            })()}
          </div>
        </>
      )}

      <div className="mt-5 pt-5 border-t border-gray-100">
        <SortingSection sortField={sortField} sortOrder={sortOrder} onSortChange={onSortChange} />
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
      href={`https://www.gcores.com/radios/${episode.id}`}
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
  const [userIds, setUserIds] = useState([]);
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
        if (userIds.length) params.append('user_id', userIds.join(','));
        if (categoryId) params.append('category_id', categoryId.toString());
        if (albumId) params.append('album_id', albumId.toString());
        if (sortField) {
          params.append('sort_field_str', sortField);
          params.append('asc', (!sortOrder).toString());
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
        <div className="flex items-center justify-end gap-3 mb-3 text-xs text-gray-400">
          <span>非商业项目，内容版权归机核网所有</span>
          <a href="https://github.com/GabrielDrapor/jcores" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" /></svg>
          </a>
        </div>
        <FilterSection
          users={users}
          categories={categories}
          albums={albums}
          selectedUserIds={userIds}
          selectedCategoryId={categoryId}
          selectedAlbumId={albumId}
          sortField={sortField}
          sortOrder={sortOrder}
          onUserSelect={(id) => {
            const newIds = userIds.includes(id) ? userIds.filter(x => x !== id) : [...userIds, id];
            setUserIds(newIds);
            const params = new URLSearchParams();
            if (newIds.length) params.append('user_id', newIds.join(','));
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
            if (userIds.length) params.append('user_id', userIds.join(','));
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
            if (userIds.length) params.append('user_id', userIds.join(','));
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
            if (userIds.length) params.append('user_id', userIds.join(','));
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
