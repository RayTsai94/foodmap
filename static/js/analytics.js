// GA 事件追蹤函數
const Analytics = {
    // 追蹤餐廳評分
    trackRating: function(restaurantName, rating) {
        gtag('event', 'rate_restaurant', {
            'restaurant_name': restaurantName,
            'rating': rating
        });
    },

    // 追蹤打卡
    trackCheckin: function(restaurantName, item, price) {
        gtag('event', 'checkin', {
            'restaurant_name': restaurantName,
            'item': item,
            'price': price
        });
    },

    // 追蹤搜尋
    trackSearch: function(searchTerm, category) {
        gtag('event', 'search', {
            'search_term': searchTerm,
            'category': category
        });
    },

    // 追蹤文章發布
    trackArticlePublish: function(articleTitle) {
        gtag('event', 'publish_article', {
            'article_title': articleTitle
        });
    },

    // 追蹤評論發布
    trackCommentPost: function(articleTitle) {
        gtag('event', 'post_comment', {
            'article_title': articleTitle
        });
    },

    // 追蹤餐廳詳情頁面查看
    trackRestaurantView: function(restaurantName) {
        gtag('event', 'view_restaurant', {
            'restaurant_name': restaurantName
        });
    },

    // 追蹤菜單項目查看
    trackMenuItemView: function(restaurantName, itemName) {
        gtag('event', 'view_menu_item', {
            'restaurant_name': restaurantName,
            'item_name': itemName
        });
    },

    // 追蹤用戶互動
    trackUserInteraction: function(action, category) {
        gtag('event', 'user_interaction', {
            'action': action,
            'category': category
        });
    }
}; 