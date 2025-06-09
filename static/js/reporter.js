import { twDistricts } from './data/twdistricts_data.js';
document.addEventListener("DOMContentLoaded", function () {
  const citySelect = document.getElementById("city");
  const districtSelect = document.getElementById("district");
  const detailInput = document.getElementById("detail-address");
  const fullLocation = document.getElementById("full-location");



  // 載入縣市
  Object.keys(twDistricts).forEach(city => {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    citySelect.appendChild(option);
  });

  // 當縣市變更時，更新行政區
  citySelect.addEventListener("change", () => {
    const city = citySelect.value;
    const districts = twDistricts[city] || [];
    districtSelect.innerHTML = '<option value="">請選擇</option>';
    districtSelect.disabled = districts.length === 0;

    districts.forEach(dist => {
      const option = document.createElement("option");
      option.value = dist;
      option.textContent = dist;
      districtSelect.appendChild(option);
    });

    updateFullLocation();
  });

  // 更新完整地址
  districtSelect.addEventListener("change", updateFullLocation);

  function updateFullLocation() {
    const city = citySelect.value;
    const district = districtSelect.value;
    if (city && district) {
      fullLocation.value = `${city} ${district}`;
    }
  }
});

document.getElementById("report-form").addEventListener("submit", async (e) => {
  e.preventDefault(); // 阻止預設送出行為

  const form = e.target;
  const formData = new FormData(form);

  // 拼接 location 欄位（縣市 + 區 + 詳細地址）
  const city = form.city.value;
  const district = form.district.value;
  const detailAddress = document.getElementById("detail-address").value;
  const fullLocation = `${city} ${district} ${detailAddress}`;
  formData.set("location", fullLocation);

  try {
    const res = await fetch("/reporter", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("上傳失敗");

    const data = await res.json();

    // ✅ 更新歷史紀錄表格
    const tbody = document.getElementById("report-table-body");
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td>new</td>
      <td>待救援</td>
      <td>${data.formatted_time}</td>
      <td>${data.location}</td>
      <td>${data.status}</td>
      <td>${data.description}</td>
      <td><img src="${data.cat_photo}" alt="貓咪照" class="max-w-[80px] mx-auto"></td>
      <td><img src="${data.env_photo}" alt="環境照" class="max-w-[80px] mx-auto"></td>
    `;
    tbody.prepend(newRow);

    // ✅ 清空表單（可選）
    form.reset();
    alert("通報成功！");
  } catch (err) {
    console.error(err);
    alert("通報失敗，請稍後再試！");
  }
});
