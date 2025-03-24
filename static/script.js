// Session management
let currentSession = localStorage.getItem('sessionId') || null;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('postForm')) initSharePage();
    if (document.getElementById('postsContainer')) initCommunityPage();
});

// Share Page Logic
function initSharePage() {
    const form = document.getElementById('postForm');
    const responseSection = document.getElementById('responseSection');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const content = formData.get('content');
        const emotion = formData.get('emotion');

        console.log('Form submitted:', { content, emotion, session_id: currentSession });

        try {
            const response = await fetch('/api/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, emotion, session_id: currentSession })
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.detail || 'Failed to submit post.');
                return;
            }

            const data = await response.json();

            if (!currentSession) {
                currentSession = data.session_id;
                localStorage.setItem('sessionId', currentSession);
            }

            displayPostResponse(data);
            responseSection.classList.remove('hidden');

        } catch (error) {
            console.error('JS Error:', error);
            alert('Failed to submit post. Please try again.');
        }
    });
}

function displayPostResponse(data) {
    document.getElementById('aiResponse').textContent = data.ai_response;

    const similarPosts = document.getElementById('similarPosts');
    similarPosts.innerHTML = data.similar_posts.length > 0
        ? data.similar_posts.map(createPostCard).join('')
        : '<p>No similar posts found yet.</p>';

    const suggestions = document.getElementById('suggestions');
    suggestions.innerHTML = data.suggestions.map(s => `<li>${s}</li>`).join('');
}

// Community Page Logic
function initCommunityPage() {
    loadCommunityPosts();

    document.getElementById('filterBtn').addEventListener('click', () => {
        const emotion = document.getElementById('emotionFilter').value;
        loadCommunityPosts(emotion);
    });
}

async function loadCommunityPosts(emotion = null) {
    try {
        const url = emotion ? `/api/posts?emotion=${emotion}` : '/api/posts';
        const response = await fetch(url);
        const posts = await response.json();

        document.getElementById('postsContainer').innerHTML =
            posts.length > 0
                ? posts.map(createPostCard).join('')
                : '<p>No posts found. Be the first to share!</p>';

    } catch (error) {
        console.error('Error loading posts:', error);
    }
}

function createPostCard(post) {
    return `
        <div class="post-card" data-post-id="${post.post_id}">
            <img src="/static/assets/${post.emotion || 'neutral'}.svg" class="post-emotion">
            <div class="post-content">${post.content}</div>
            <div class="post-footer">
                <span>${new Date(post.timestamp).toLocaleDateString()}</span>
                <button class="upvote-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24">
                        <path d="M12 19V5M5 12l7-7 7 7"/>
                    </svg>
                    ${post.upvotes || 0}
                </button>
            </div>
        </div>
    `;
}

// Upvote handling
document.addEventListener('click', async (e) => {
    if (e.target.closest('.upvote-btn')) {
        const postId = e.target.closest('.post-card').dataset.postId;
        try {
            const response = await fetch(`/api/posts/${postId}/upvote`, { method: 'POST' });
            const data = await response.json();

            const btn = e.target.closest('.upvote-btn');
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24">
                    <path d="M12 19V5M5 12l7-7 7 7"/>
                </svg>
                ${data.upvotes}
            `;

        } catch (error) {
            console.error('Error upvoting:', error);
        }
    }
});