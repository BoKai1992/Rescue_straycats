//console.log("index.js loaded");
// modal 控制
function showModal(id) {
  document.getElementById(id).classList.remove('hidden');
}
function hideModal(id) {
  document.getElementById(id).classList.add('hidden');
}

// 🐱 輪播邏輯
const images = [
    "/static/cats/cat1.jpg", "/static/cats/cat2.jpg", "/static/cats/cat3.jpg",
    "/static/cats/cat4.jpg", "/static/cats/cat5.jpg"
];
let current = 0;
const imgElement = document.getElementById("cat-carousel");

if (imgElement) {
  setInterval(() => {
    current = (current + 1) % images.length;
    imgElement.style.opacity = 0;
    setTimeout(() => {
      imgElement.src = images[current];
      imgElement.style.opacity = 1;
    }, 300);
  }, 4000);
}
