<template>
  <div class="modal fade" ref="editCardModal" tabindex="-1" aria-labelledby="editCardModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="editCardModalLabel">Edit: {{ cardToEdit.card_name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form v-if="editableCard" @submit.prevent="submitUpdate">
            <div class="mb-3">
              <label for="editCardAmount" class="form-label">Amount</label>
              <input type="number" class="form-control" id="editCardAmount" v-model.number="editableCard.amount" min="1" required>
            </div>
            <h6 class="mt-4">Specifications</h6>
            <p class="text-muted small">Currently, only editing the first specification is supported.</p>
            <div class="mb-3">
              <label for="edit_set_code" class="form-label">Set Code</label>
              <input type="text" class="form-control" id="edit_set_code" v-model="editableCard.specifications[0].set_code">
            </div>
            <div class="mb-3">
              <label for="edit_collector_number" class="form-label">Collector Number</label>
              <input type="text" class="form-control" id="edit_collector_number" v-model="editableCard.specifications[0].collector_number">
            </div>
            <div class="mb-3">
              <label for="edit_finish" class="form-label">Finish</label>
              <select class="form-select" id="edit_finish" v-model="editableCard.specifications[0].finish">
                <option value="non-foil">Non-Foil</option>
                <option value="foil">Foil</option>
                <option value="etched">Etched</option>
              </select>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" @click="submitUpdate">Save Changes</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, defineEmits, defineExpose } from 'vue';
import { Modal } from 'bootstrap';

const props = defineProps({
  cardToEdit: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['update-card']);

const editCardModal = ref(null);
let modalInstance = null;

const editableCard = ref(null);

// When the modal is shown, populate the form with the prop data

function submitUpdate() {
  const payload = {
    card: props.cardToEdit.card_name, // The original name to find the card
    update_data: {
      amount: editableCard.value.amount,
      specifications: [editableCard.value.specifications[0]] // The UI only supports editing the first spec
    }
  };
  emit('update-card', payload);
  modalInstance.hide();
}

function show() {
  // Deep copy to avoid mutating the prop directly
  editableCard.value = JSON.parse(JSON.stringify(props.cardToEdit));
  // Ensure specifications is an array with at least one object for the form
  if (!editableCard.value.specifications || editableCard.value.specifications.length === 0) {
    editableCard.value.specifications = [{ set_code: '', collector_number: '', finish: 'non-foil' }];
  }
  modalInstance.show();
}

onMounted(() => {
  modalInstance = new Modal(editCardModal.value);
});

defineExpose({
  show
});
</script>