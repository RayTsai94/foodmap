// 初始化全局變數
let map;
let markers = [];
let infoWindow;

// 初始化地圖
function initializeMap() {
    // 設置中央大學的座標位置
    const ncuLocation = { lat: 24.9677, lng: 121.1892 };
    
    // 創建地圖
    map = new google.maps.Map(document.getElementById('restaurant-map'), {
        center: ncuLocation,
        zoom: 15,
        styles: mapStyles,
        mapTypeControl: false,
        fullscreenControl: true,
        streetViewControl: false,
        zoomControl: true
    });
    
    // 創建信息窗口
    infoWindow = new google.maps.InfoWindow();
    
    // 添加中央大學標記
    const ncuMarker = new google.maps.Marker({
        position: ncuLocation,
        map: map,
        title: '國立中央大學',
        icon: {
            url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
        },
        zIndex: 999
    });
    
    // 添加餐廳標記
    if (typeof restaurantLocations !== 'undefined' && restaurantLocations.length > 0) {
        restaurantLocations.forEach(restaurant => {
            addMarker(restaurant);
        });
    }
}

// 添加標記函數
function addMarker(restaurant) {
    if (restaurant.lat && restaurant.lng) {
        const position = { lat: restaurant.lat, lng: restaurant.lng };
        
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: restaurant.name,
            restaurantId: restaurant.id
        });
        
        marker.addListener('click', () => {
            // 創建信息窗口內容
            const contentString = `
                <div class="map-info-window">
                    <h5>${restaurant.name}</h5>
                    <p>${restaurant.address}</p>
                    <a href="/restaurants/${restaurant.id}/" class="btn btn-sm btn-primary">查看詳情</a>
                </div>
            `;
            
            infoWindow.setContent(contentString);
            infoWindow.open(map, marker);
        });
        
        markers.push(marker);
    }
}

// 自訂地圖樣式
const mapStyles = [
    {
        "featureType": "poi.business",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "poi.park",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    }
];

// 文件加載後執行
document.addEventListener('DOMContentLoaded', function() {
    // 為評論表單添加評分選擇功能
    const ratingInputs = document.querySelectorAll('.rating-input');
    const ratingValue = document.getElementById('rating-value');
    const ratingStars = document.querySelectorAll('.rating-star');
    
    if (ratingStars.length > 0) {
        ratingStars.forEach(star => {
            star.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                ratingValue.value = value;
                
                // 更新星星顯示
                ratingStars.forEach(s => {
                    if (s.getAttribute('data-value') <= value) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
            });
        });
    }
    
    // 為菜單過濾器添加功能
    const menuFilter = document.getElementById('menu-filter');
    const menuItems = document.querySelectorAll('.menu-item');
    
    if (menuFilter && menuItems.length > 0) {
        menuFilter.addEventListener('change', function() {
            const filterValue = this.value;
            
            menuItems.forEach(item => {
                if (filterValue === 'all' || item.getAttribute('data-category') === filterValue) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // 為餐廳過濾表單添加自動提交功能
    const filterForms = document.querySelectorAll('.filter-form select, .filter-form input[type="radio"]');
    
    if (filterForms.length > 0) {
        filterForms.forEach(element => {
            element.addEventListener('change', function() {
                this.closest('form').submit();
            });
        });
    }
    
    // 為分析頁面的圖表初始化
    if (document.getElementById('caloriesChart')) {
        initializeCharts();
    }
});

// 初始化圖表函數
function initializeCharts() {
    // 這裡會添加營養分析頁面的圖表初始化代碼
    console.log('Charts initialized');
}

// 驗證評論表單
function validateReviewForm() {
    const ratingValue = document.getElementById('rating-value').value;
    const commentText = document.getElementById('id_comment').value;
    
    if (ratingValue === '0') {
        alert('請選擇評分');
        return false;
    }
    
    if (commentText.trim() === '') {
        alert('請輸入評論內容');
        return false;
    }
    
    return true;
} 