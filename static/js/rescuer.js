import { twDistricts } from './data/twdistricts_data.js';

function populateCities() {
  const citySelect = document.getElementById("city");
  const selected = citySelect.getAttribute("data-selected") || "";
  citySelect.innerHTML = '<option value="">--選擇縣市--</option>';
  Object.keys(twDistricts).forEach(c => {
    const sel = c === selected ? "selected" : "";
    citySelect.innerHTML += `<option value="${c}" ${sel}>${c}</option>`;
  });
}

function updateDistricts() {
  const city = document.getElementById("city").value;
  const dselect = document.getElementById("district");
  const selected = dselect.getAttribute("data-selected") || "";
  dselect.innerHTML = '<option value="">--選擇區域--</option>';
  if (Array.isArray(twDistricts[city])) {
    twDistricts[city].forEach(d => {
      const sel = d === selected ? "selected" : "";
      dselect.innerHTML += `<option value="${d}" ${sel}>${d}</option>`;
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  populateCities();
  updateDistricts();
  document.getElementById("city").addEventListener("change", updateDistricts);
});


window.updateStatus = async function (id, btn) {
  try {
    const res = await fetch(`/update_status/${id}`, { method: "POST" });
    const result = await res.json();

    if (result.success) {
      const row = btn.closest("tr");

      // 更新狀態顯示並移除按鈕
      row.querySelector(".status").innerText = "已救援";
      btn.remove();

      // 取得所需欄位資料
      const time = row.querySelector(".rescue-time")?.innerText || "";
      const location = row.querySelector(".rescue-location")?.innerText || "";
      const catStatus = row.querySelector(".cat-status")?.innerText || "";
      const description = row.querySelector(".env-description")?.innerText || "";
      const catImg = row.querySelector(".cat-photo")?.innerHTML || "";
      const envImg = row.querySelector(".env-photo")?.innerHTML || "";

      // 建立新列
      const newRow = document.createElement("tr");
      newRow.innerHTML = `
        <td class="w-[60px] truncate px-4 py-2">-</td>
        <td class="w-[80px] px-4 py-2">${time}</td>
        <td class="w-[220px] px-4 py-2">${location}</td>
        <td class="w-[100px] px-4 py-2">${catStatus}</td>
        <td class="w-[200px] px-4 py-2">${description}</td>
        <td class="w-[100px] px-4 py-2">${catImg}</td>
        <td class="w-[100px] px-4 py-2">${envImg}</td>
      `;

      // 插入歷史紀錄表格最上方
      const historyTable = document.getElementById("rescued-history-table");
      if (historyTable) {
        historyTable.insertBefore(newRow, historyTable.firstChild);
        reindexTable("#rescued-history-table");
      }

      // 移除原本這列
      row.remove();
    } else {
      alert("更新失敗！");
    }
  } catch (e) {
    console.error(e);
    alert("伺服器錯誤");
  }
};

// 自動編號
function reindexTable(selector) {
  const rows = document.querySelectorAll(`${selector} tr`);
  rows.forEach((tr, i) => {
    const firstCell = tr.querySelector("td");
    if (firstCell) firstCell.textContent = i + 1;
  });
}


