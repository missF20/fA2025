import React from 'react';
import { Row, Col } from 'react-bootstrap';

interface ConversationHeaderProps {
  title?: string;
}

/**
 * Header component for conversations dashboard
 */
const ConversationHeader: React.FC<ConversationHeaderProps> = ({ title = 'Conversations' }) => {
  return (
    <Row className="mb-4 align-items-center">
      <Col>
        <h1 className="mb-0">{title}</h1>
      </Col>
    </Row>
  );
};

export default ConversationHeader;