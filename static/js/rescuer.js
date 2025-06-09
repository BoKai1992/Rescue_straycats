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

window.onload = () => {
  populateCities();
  updateDistricts();
  document.getElementById("city").addEventListener("change", updateDistricts);
};

window.updateStatus = async function (id, btn) {
  try {
    console.log("發送 rescue id：", id);
    const res = await fetch(`/update_status/${id}`, { method: "POST" });
    const result = await res.json();

    if (result.success) {
      const row = btn.closest("tr");
      row.querySelector(".status").innerText = "已救援";
      btn.remove();

      const history = document.getElementById("rescued-history-table");
      if (history) {
        const newRow = row.cloneNode(true);
        newRow.children[2].innerHTML = "-";
        history.insertBefore(newRow, history.firstChild);
        row.remove();
      }
    } else {
      alert("更新失敗！");
    }
  } catch (e) {
    console.error(e);
    alert("伺服器錯誤");
  }
};

