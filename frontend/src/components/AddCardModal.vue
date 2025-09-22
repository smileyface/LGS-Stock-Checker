<template>
  <div class="modal fade" ref="addCardModal" tabindex="-1" aria-labelledby="addCardModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="addCardModalLabel">Add New Card</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitCard">
            <div class="mb-3">
              <label for="cardName" class="form-label">Card Name</label>
              <input type="text" class="form-control" id="cardName" v-model="card.name" list="cardNameDatalist" required>
              <datalist id="cardNameDatalist">
                <option v-for="name in allCardNames" :key="name" :value="name"></option>
              </datalist>
            </div>
            <div class="mb-3">
              <label for="cardAmount" class="form-label">Amount</label>
              <input type="number" class="form-control" id="cardAmount" v-model.number="card.amount" min="1" required>
            </div>
            <h6 class="mt-4">Optional Specifications</h6>
            <div class="mb-3">
              <label for="set_code" class="form-label">Set Code</label>
              <input type="text" class="form-control" id="set_code" v-model="card.specs.set_code">
            </div>
            <div class="mb-3">
              <label for="collector_number" class="form-label">Collector Number</label>
              <input type="text" class="form-control" id="collector_number" v-model="card.specs.collector_number">
            </div>
            <div class="mb-3">
              <label for="finish" class="form-label">Finish</label>
              <select class="form-select" id="finish" v-model="card.specs.finish">
                <option value="non-foil">Non-Foil</option>
                <option value="foil">Foil</option>
                <option value="etched">Etched</option>
              </select>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" @click="submitCard">Add Card</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineEmits, defineExpose } from 'vue';
import { Modal } from 'bootstrap';
import { io } from 'socket.io-client';

const emit = defineEmits(['save-card']);
const socket = io({ withCredentials: true });

const addCardModal = ref(null);
let modalInstance = null;

const allCardNames = ref([]);
const card = ref({
  name: '',
  amount: 1,
  specs: {
    set_code: '',
    collector_number: '',
    finish: 'non-foil'
  }
});

onMounted(() => {
  modalInstance = new Modal(addCardModal.value);
  
  socket.emit('request_card_names');
  socket.on('card_names_response', (data) => {
    allCardNames.value = data.card_names || [];
  });
});

function submitCard() {
  const payload = {
    card: card.value.name,
    amount: card.value.amount,
    card_specs: card.value.specs
  };
  emit('save-card', payload);
  modalInstance.hide();
}

defineExpose({
  show: () => modalInstance.show()
});
</script>
